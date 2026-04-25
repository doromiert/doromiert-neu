{
  description = "doromiert personal site";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      apps.${system}.default = {
        type = "app";
        program = toString (
          pkgs.writeShellScript "dev" ''
            set -e
            cd "/home/doromiert/Projects/doromiert-neu"

            echo ":: initial build"
            ${pkgs.python3}/bin/python3 build.py

            echo ":: watching — http://localhost:8080"

            ${pkgs.watchexec}/bin/watchexec \
              --watch index.html \
              --watch icons.txt \
              --watch icons.svg \
              --watch doromiert.svg \
              --on-busy-update restart \
              --postpone \
              -- ${pkgs.python3}/bin/python3 build.py &

            WATCHPID=$!
            trap "kill $WATCHPID 2>/dev/null" EXIT

            exec ${pkgs.browser-sync}/bin/browser-sync start \
              --server dist \
              --files "dist/**" \
              --port 8080 \
              --no-notify \
              --no-ui
          ''
        );
      };
    };
}
