# Shopify Alexa Skill
![status](https://img.shields.io/badge/status-ready%20to%20use-green)

Alexa skill to tell you interesting things about recent orders in your Shopify store.

For example,

>"Alexa, ask my shop, 
>>how many orders have I had today?"
>>
>>how many orders were there yesterday?
>>
>>gross sales today."
>>
>>gross sales amount yesterday."
>>
>>tell me about the most recent order."

#### Installation
```
pip install requests
pip install python-dotenv
pip install pytz
```
See `requirements.txt` for details.

#### Private app set up in Shopify
* TODO - what API does it need access to.

#### Environment config
The script needs a `.env` file like this,
```
# Timezone of AWS server. From list at https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
SERVER_TIMEZONE=<your timezone>

# Shopify
SHOP_NAME=<your shop name>
API_VERSION=<your Shopify API version>
API_KEY=<your API key>
PASSWORD=<your password>
```
#### TODO
* Make paginated requests to the Shopify REST Admin API. This will allow the skill to exceed current limit of 250 orders in last 3 days.

#### Useful links
Python [Shopify API](https://github.com/Shopify/shopify_python_api)
