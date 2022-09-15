from http import HTTPStatus
import requests

# sequential test case
# check whether the quantity of the item is decreased accordingly in the restaurant after the order has successfuly placed (unassigned)

# RESTAURANT SERVICE    : http://localhost:8080
# DELIVERY SERVICE      : http://localhost:8081
# WALLET SERVICE        : http://localhost:8082

def assureAllAgentSignOut():
    """required after renitializing delivery"""
    agents = [201, 202, 203]
    for agent in agents:
        # wait till status becomes signed-out
        while True:
            http_response = requests.get(f"http://localhost:8081/agent/{agent}")
            agent_status = http_response.json().get("status")
            if agent_status=="signed-out": break

def test():

    # Reinitialize Restaurant service
    http_response = requests.post("http://localhost:8080/reInitialize")

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    # Reinitialize Delivery service
    http_response = requests.post("http://localhost:8081/reInitialize")

    assureAllAgentSignOut()


    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    # Reinitialize Wallet service
    http_response = requests.post("http://localhost:8082/reInitialize")

    if(http_response.status_code != HTTPStatus.CREATED):
        return 'Fail'

    # Customer 301 requests an order of item 1, quantity 10 from restaurant 102
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 301, "restId": 102, "itemId": 1, "qty": 10})

    if(http_response.status_code != 201):
        print(http_response.status_code)
        return 'Fail'

    # check orderId
    orderId = http_response.json().get("orderId")
    if orderId != 1000:
        return 'Fail'

    # check status of order, this will also ensure that all wallet and restaurant related tasks of /requestOrder endpoint are completed
    http_response = requests.get(f"http://localhost:8081/order/{orderId}")
    if(http_response.status_code != HTTPStatus.OK):
        return 'Fail'

    res_body = http_response.json()
    if res_body.get("orderId")!=orderId or res_body.get("status")!="unassigned":
        return 'Fail'


    # Customer 302 requests an order of item 1, quantity 1 from restaurant 102, this order should be rejeted if quantity was correctly updated
    http_response = requests.post(
        "http://localhost:8081/requestOrder", json={"custId": 302, "restId": 102, "itemId": 1, "qty": 1})

    if(http_response.status_code != 201):
        return 'Fail'

    # check status of order 1001, this will also ensure that all wallet and restaurant related tasks of /requestOrder endpoint are completed
    http_response = requests.get(f"http://localhost:8081/order/1001")
    if(http_response.status_code != HTTPStatus.OK):
        return 'Fail'

    res_body = http_response.json()
    if res_body.get("orderId")!=1001 or res_body.get("status")!="rejected":
        return 'Fail'

    return 'Pass'


if __name__ == "__main__":
    test_result = test()
    print(test_result)
