import os

def create_your_secrets(api_key: str, filename: str = "config.toml"):

    with open(filename, "w") as f:
        f.write(f"GOOGLE_API_KEY = \"{api_key}\"")

    print(f"Secrets file created at {filename}")
        
if __name__ == "__main__":
    while True:
        api_key = input("Enter your API key: ").strip()
        
        if api_key:
            create_your_secrets(api_key)
            break
        else:
            print("Please insert a valid API Key (cannot be empty)")