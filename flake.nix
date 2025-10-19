{
  description = "Python application flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        runtimeDeps = with pkgs.python3Packages; [ledger];
        buildDeps = with pkgs.python3Packages; [setuptools];
        devDeps = with pkgs.python3Packages; [pandas pandas-stubs xlrd];
      in {
        packages.default = pkgs.python3Packages.buildPythonApplication {
          pname = "ledger-jester";
          version = "0.1";
          pyproject = true;
          dependencies = runtimeDeps ++ buildDeps;
          src = ./.;
          dontCheckRuntimeDeps = true;
        };
        devShells.default = pkgs.mkShell {buildInputs = runtimeDeps ++ devDeps;};
      }
    );
}
