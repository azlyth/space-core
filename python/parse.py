import ast
import os
import pdb
import sys
from dataclasses import dataclass


SOURCE_DIRECTORY = sys.argv[1]


@dataclass
class Function:
    ast_object: ast.FunctionDef
    path: str

    def name(self):
        return self.ast_object.name

    def calls(self):
        return [n for n in ast.walk(self.ast_object) if isinstance(n, ast.Call)]


@dataclass
class Class:
    ast_object: ast.ClassDef
    path: str

    def name(self):
        return self.ast_object.name

    def methods(self):
        return [
            Function(ast_object=n, path=self.path)
            for n in self.ast_object.body
            if isinstance(n, ast.FunctionDef)
        ]


@dataclass
class CodeFile:
    path: str

    @property
    def ast_object(self):
        with open(self.path) as file:
            node = ast.parse(file.read())
        return node

    def functions(self):
        return [
            Function(ast_object=n, path=self.path)
            for n in self.ast_object.body
            if isinstance(n, ast.FunctionDef)
        ]

    def classes(self):
        return [
            Class(ast_object=n, path=self.path)
            for n in self.ast_object.body
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
        return sum([pf.classes() for pf in cb.code_files()], [])

    def all_functions(self):
        return sum([pf.functions() for pf in cb.code_files()], [])


if __name__ == "__main__":
    cb = Codebase(sys.argv[1])
    print([x.name() for x in cb.all_functions()])
    print([x.name() for x in cb.all_classes()])
