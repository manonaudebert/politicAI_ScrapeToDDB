import requests
from bs4 import BeautifulSoup
import json
import boto3
import uuid

# Bedrock Runtime client used to invoke and question the models
bedrock_runtime = boto3.client(
     service_name='bedrock-runtime', 
     region_name='us-east-1'
    )
dynamodb = boto3.resource('dynamodb')

def get_topic_classification(promise):
    modelId = 'ai21.j2-ultra-v1'

    # The payload to be provided to Bedrock 
    prompt = f'''{promise}. Which sector does this statement fit into? Please only provide the sector name in the response.
    [Infrastructure, Taxes, Healthcare, Technology, War, International_Policy, Immigration, Education, Climate_Change, Economy, 
    Social_Welfare, Housing, Justice_and_Law_Enforcement, Civil_Rights]'''
    body = json.dumps(
       {
          "prompt": prompt, 
          "maxTokens": 20,
          "temperature": 0.2,
          "topP": 0.3,
       }
     )
    # The actual call to retrieve an answer from the model
    response = bedrock_runtime.invoke_model(
       body=body, 
       modelId=modelId, 
       accept='application/json', 
       contentType='application/json'
     )
    
    response_body = json.loads(response.get('body').read())
    topic = response_body.get('completions')[0].get('data').get('text').strip()
    return topic


def get_status(class_list):
    if 'm-statement--true' in class_list:
        return 'Kept'
    elif 'm-statement--half-true' in class_list:
        return 'Blocked'
    elif 'm-statement--false' in class_list:
        return 'Broken'
    elif 'm-statement--spectr' in class_list:
        return 'Kept'
    else:
        return 'Unknown'

def scrape_politifact(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    promises = []
    for item in soup.find_all('div', class_='o-listing__item'):
        article_tag = item.find('article')
        class_list = article_tag.get('class', [])  # Get the class list, default to empty if not present
        text = article_tag.find('div', class_='m-statement__quote').text.strip()
        status = get_status(class_list)
        promises.append({'promise': text, 'status': status})

    return promises

def lambda_handler(event, context):
        try:
            politician_fname = 'Joe'
            politician_lname = 'Biden'
            affiliation = 'Democrat'
            office = 'President'
            url = "https://www.politifact.com/truth-o-meter/promises/biden-promise-tracker/?ruling=true"
            promises = scrape_politifact(url)
            table = dynamodb.Table('campaign_promises_by_topic')
            promises_by_topic = {}
            for promise in promises:
                topic = get_topic_classification(promise)
                topic_string = f'{{"promise": "{promise.get("promise")}", "status": "{promise.get("status")}"}}'
                if topic in promises_by_topic:
                    promises_by_topic[topic].append(topic_string)
                else:
                    promises_by_topic[topic] = [topic_string]

            for topic in promises_by_topic:
                promise_details = {
                "key": f"{politician_lname}_{topic}",
                "politician_fname": politician_fname,
                "politician_lname": politician_lname,
                "affiliation": affiliation,
                "public_office": office,
                "promise_status": promises_by_topic[topic],
                "topic_class": topic
                }

                table.put_item(Item=promise_details)


            return {
            'statusCode': 200,
            'body': json.dumps('Done!')
            }
        except Exception as e:
            print(f"An error occurred: {e}")

