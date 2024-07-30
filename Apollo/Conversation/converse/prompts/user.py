

class PromptMaker:

    def __init__(self, prompt_config={}, separator="\n\n") -> None:
        self.prompt_config = self.validate_and_normalize_prompt_config(prompt_config)
        self.separator = str(separator)


    def validate_and_normalize_prompt_config(self, prompt_config: dict):

        if not isinstance(prompt_config, dict): raise TypeError()

        prompt_config_normalized = {}
        for key in prompt_config:
            config = prompt_config[key]
            if not config: raise ValueError()
            if not isinstance(config, dict): raise TypeError()
            if not config.get("label", None): raise ValueError()

            prompt_config_normalized.update({
                key: {
                    "label": config.get("label"),
                    "delimiter": config.get("delimiter", ":\n"),
                    "value": config.get("value", "")
                }
            })

        return prompt_config_normalized


    def get(self, context: dict):

        results = []

        # if key in context: value = str(context.get(key))

        if not context:
            for key, config in self.prompt_config.items():
                results.append(f'{config.get("label")}{config.get("delimiter")}{config.get("value")}')

        else:
            for key, value in context.items():
                if key not in self.prompt_config: continue
                config = self.prompt_config[key]
                results.append(f'{config.get("label")}{config.get("delimiter")}{value}')

        return self.separator.join(results)
    



