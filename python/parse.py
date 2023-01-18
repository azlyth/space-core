import ast
import os
import pdb
import sys
from dataclasses import dataclass
from pprint import pprint
from typing import Optional


SOURCE_DIRECTORY = sys.argv[1]


def test_method():
    return os.path.exists("/tmp")


def flatten(_list):
    return sum(_list, [])


@dataclass
class Attribute:
    ast: ast.Attribute
    path: str

    def short_name(self):
        child = self.ast.value
        if isinstance(child, ast.Name):
            if self.ast.attr:
                return self.ast.attr
            else:
                return child.id
        elif isinstance(child, ast.Attribute):
            return self.ast.attr

    def full_name(self):
        child = self.ast.value
        if isinstance(child, ast.Name):
            if self.ast.attr:
                return f"{child.id}.{self.ast.attr}"
            else:
                return child.id
        elif isinstance(child, ast.Attribute):
            return f"{Attribute(ast=child, path=self.path).full_name()}.{self.ast.attr}"


@dataclass
class Class:
    ast: ast.ClassDef
    path: str

    def name(self):
        return self.ast.name

    def methods(self):
        return [
            Function(ast=n, path=self.path, parent=self)
            for n in self.ast.body
            if isinstance(n, ast.FunctionDef)
        ]


@dataclass
class Function:
    ast: ast.FunctionDef
    path: str
    parent: Optional[Class] = None

    def short_name(self):
        return self.ast.name

    def full_name(self):
        if self.parent:
            return f"{self.parent.name()}.{self.short_name()}"
        else:
            return self.ast.name

    def calls(self):
        return [
            Call(ast=n, path=self.path, parent=self)
            for n in ast.walk(self.ast)
            if isinstance(n, ast.Call)
        ]


@dataclass
class Call:
    parent: Function
    ast: ast.Call
    path: str

    def full_name(self):
        func = self.ast.func
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return Attribute(ast=func, path=self.path).full_name()

    def short_name(self):
        func = self.ast.func
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return Attribute(ast=func, path=self.path).short_name()


@dataclass
class CodeFile:
    path: str

    @property
    def ast(self):
        with open(self.path) as file:
            node = ast.parse(file.read())
        return node

    def functions(self):
        return [
            Function(ast=n, path=self.path)
            for n in self.ast.body
            if isinstance(n, ast.FunctionDef)
        ]

    def classes(self):
        return [
            Class(ast=n, path=self.path)
            for n in self.ast.body
            if isinstance(n, ast.ClassDef)
        ]


@dataclass
class Codebase:
    path: str

    def code_file_paths(self):
        paths = []
        for dirpath, dirnames, filenames in os.walk(self.path):
            for fn in filenames:
                path = os.path.join(dirpath, fn)
                if path.endswith(".py"):
                    paths.append(path)
        return paths

    def code_files(self):
        return [CodeFile(p) for p in self.code_file_paths()]

    def all_classes(self):
        return flatten([pf.classes() for pf in self.code_files()])

    def all_functions(self):
        return flatten([pf.functions() for pf in self.code_files()])

    def all_calls(self):
        return flatten(
            [flatten([m.calls() for m in c.methods()]) for c in self.all_classes()]
        ) + flatten([f.calls() for f in self.all_functions()])

    def print_all(self):
        print(">> Class-less functions\n")
        pprint([x.full_name() for x in self.all_functions()])

        print("\n>> Classes, methods, and calls")
        for x in self.all_classes():
            print(f"\nCLASS: {x.name()}")
            pprint(
                [
                    (x.full_name(), [c.full_name() for c in x.calls()])
                    for x in x.methods()
                ]
            )


if __name__ == "__main__":
    cb = Codebase(sys.argv[1])
    cb.print_all()

    functions = {
        f.short_name(): {"object": f, "callers": []}
        for f in cb.all_functions() + flatten([c.methods() for c in cb.all_classes()])
    }

    for call in cb.all_calls():
        if call.short_name() in functions:
            functions[call.short_name()]["callers"].append(call)

    print("\n>> List of methods and who calls them\n")
    for function_name, data in functions.items():
        print(
            data["object"].full_name(), [c.parent.full_name() for c in data["callers"]]
        )

    # pdb.set_trace()
