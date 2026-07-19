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
        parserDeps = with pkgs.python3.pkgs; [pandas];
      in {
        packages.default = pkgs.python3Packages.buildPythonApplication {
          pname = "ledger-jester";
          version = "0-unstable";
          pyproject = true;
          src = ./.;
          build-system = with pkgs.python3.pkgs; [setuptools];
          optional-dependencies.parsers = parserDeps;
          nativeCheckInputs = [pkgs.python3.pkgs.pytestCheckHook] ++ parserDeps;
        };
        devShells.default = pkgs.mkShell {
          packages = [pkgs.ledger pkgs.python3.pkgs.pytest] ++ parserDeps;
        };
        treefmt = {
          projectRootFile = "flake.nix";
          programs = {
            alejandra.enable = true;
            deno.enable = true;
            ruff-check = {
              enable = true;
              extendSelect = ["I" "D"];
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
