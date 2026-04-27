{
  description = "doromiert personal site";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      pythonWithMarkdown = pkgs.python3.withPackages (ps: [ ps.markdown ps.fonttools ps.brotli ]);
    in
    {
      apps.${system} = {
        # your normal dev environment
        default = {
          type = "app";
          program = toString (
            pkgs.writeShellScript "dev" ''
              set -e
              cd "/home/doromiert/Projects/doromiert-neu"

              echo ":: initial build"
              ${pythonWithMarkdown}/bin/python3 build.py

              echo ":: watching — http://localhost:8080"

              ${pkgs.watchexec}/bin/watchexec \
                --watch index.html \
                --watch icons.txt \
                --watch icons.svg \
                --watch blog \
                --watch lib \
                --watch devices \
                --watch music \
                --watch doromiert.svg \
                --watch build.py \
                --watch base.css \
                --on-busy-update restart \
                --postpone \
                -- ${pythonWithMarkdown}/bin/python3 build.py &

              WATCHPID=$!
              trap "kill $WATCHPID 2>/dev/null" EXIT

              exec ${pkgs.browser-sync}/bin/browser-sync start \
                --server dist \
                --files "dist" \
                --port 8080 \
                --no-open
            ''
          );
        };

        # production-like environment for perf testing
        perf = {
          type = "app";
          program = toString (
            pkgs.writeShellScript "perf" ''
              set -e
              cd "/home/doromiert/Projects/doromiert-neu"

              echo ":: building clean dist"
              ${pythonWithMarkdown}/bin/python3 build.py

              echo ":: serving with caddy (gzip + zstd enabled) — http://localhost:8080"
              exec ${pkgs.caddy}/bin/caddy run --adapter caddyfile --config ${pkgs.writeText "Caddyfile" ''
                :8080 {
                  root * dist
                  encode zstd gzip
                  file_server
                }
              ''}
            ''
          );
        };
      };
    };
}
