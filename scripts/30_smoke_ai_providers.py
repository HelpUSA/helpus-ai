import os
import sys
sys.path.insert(0, os.path.abspath('backend'))
import config
expected = ['gemini', 'openrouter', 'deepseek']
print('AI_PROVIDER_ORDER=', config.AI_PROVIDER_ORDER)
assert config.AI_PROVIDER_ORDER == expected, config.AI_PROVIDER_ORDER
assert config.OPENROUTER_MODEL
assert config.DEEPSEEK_MODEL
assert config.DEEPSEEK_API_URL.startswith('https://')
assert config.AI_REVIEW_TIMEOUT > 0
print('HELPUS_PROVIDER_CONFIG_SMOKE_OK')
