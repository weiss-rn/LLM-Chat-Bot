def prompt_value(label, optional=False):
    suffix = " (optional)" if optional else ""
    value = input(f"{label}{suffix}: ").strip()
    if not value and not optional:
        print("This value is required.")
        return prompt_value(label, optional)
    return value


def write_config(values, filename="config.toml"):
    lines = []
    for key, value in values.items():
        if value:
            lines.append(f'{key} = "{value}"')
    content = "\n".join(lines)
    with open(filename, "w") as f:
        f.write(content)
    print(f"Config file created at {filename}")


if __name__ == "__main__":
    print("Create config.toml for chatbot-webv3")
    google_key = prompt_value("GOOGLE_API_KEY", optional=True)
    openai_key = prompt_value("OPENAI_API_KEY", optional=True)
    openai_base_url = prompt_value("OPENAI_BASE_URL", optional=True)
    anthropic_key = prompt_value("ANTHROPIC_API_KEY", optional=True)
    default_provider = prompt_value("CHAT_PROVIDER (google/openai/anthropic)", optional=True)
    default_model = prompt_value("GEMINI_MODEL", optional=True)

    write_config({
        "GOOGLE_API_KEY": google_key,
        "OPENAI_API_KEY": openai_key,
        "OPENAI_BASE_URL": openai_base_url,
        "ANTHROPIC_API_KEY": anthropic_key,
        "CHAT_PROVIDER": default_provider,
        "GEMINI_MODEL": default_model,
    })
