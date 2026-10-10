{
  description = "League of Analytics - Development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        inherit system;
        config.allowUnfree = true; # required for vscode
      };
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          # Python tools
          python3
          uv
          
          # Code editor
          vscode
          
          # Git hooks
          pre-commit
          
          # Additional useful tools
          git
          curl
        ];
        
        shellHook = ''
          alias vscode-web='code serve-web --host 0.0.0.0 --port 8000 --without-connection-token --accept-server-license-terms'

          echo "Development environment ready!"
          echo "Available tools: uv, vscode, pre-commit, git, curl"
          echo "Launch VS Code web UI (LAN, NO PASSWORD):"
          echo "  vscode-web"
        '';
      };
      
      packages.${system}.default = self.devShells.${system}.default;
    };
}
