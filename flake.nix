{
  description = "A stripped down fork of ledger-autosync";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs:
    inputs.flake-parts.lib.mkFlake {inherit inputs;} {
      imports = [inputs.treefmt-nix.flakeModule];
      systems = import inputs.systems;
      perSystem = {pkgs, ...}: let
        pythonSet = pkgs.python314;
        parserDeps = with pythonSet.pkgs; [lxml pandas xlrd pdfplumber];
        basePkg = pythonSet.pkgs.buildPythonApplication {
          pname = "ledger-jester";
          version = "0-unstable";
          pyproject = true;
          src = ./.;
          build-system = with pythonSet.pkgs; [setuptools];
          optional-dependencies.parsers = parserDeps;
          nativeCheckInputs = [pythonSet.pkgs.pytestCheckHook] ++ parserDeps;
        };
      in {
        packages = rec {
          base = basePkg;
          withParsers = basePkg.overridePythonAttrs (old: {
            dependencies = (old.dependencies or []) ++ parserDeps;
          });
          default = withParsers;
        };
        devShells.default = pkgs.mkShell {
          packages = [pkgs.ledger pythonSet.pkgs.pytest] ++ parserDeps;
        };
        treefmt = {
          projectRootFile = "flake.nix";
          programs = {
            alejandra.enable = true;
            deno.enable = true;
            ruff-check = {
              enable = true;
              extendSelect = ["I" "D" "ANN"];
            };
            ruff-format = {
              enable = true;
              lineLength = 79;
            };
            taplo.enable = true;
          };
        };
      };
    };
}
