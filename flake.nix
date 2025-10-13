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
        deps = with pkgs; [ledger];
        pyDeps = with pkgs.python3Packages; [ledger];
        runtimeDeps = deps ++ pyDeps;
        buildDeps = with pkgs.python3Packages; [setuptools];
        devDeps = with pkgs.python3Packages; [mypy];
      in {
        packages.default = pkgs.python3Packages.buildPythonApplication {
          pname = "foo";
          version = "0.1";
          pyproject = true;
          propagatedBuildInputs = runtimeDeps ++ buildDeps;
          src = ./.;
        };
        devShells.default = pkgs.mkShell {buildInputs = runtimeDeps ++ devDeps;};
      }
    );
}
