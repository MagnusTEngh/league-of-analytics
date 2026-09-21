{
  description = "League of Analytics - Development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs, ... }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
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
          echo "Development environment ready!"
          echo "Available tools: uv, vscode, pre-commit, git, curl"
        '';
      };
      
      packages.${system}.default = self.devShells.${system}.default;
    };
}
