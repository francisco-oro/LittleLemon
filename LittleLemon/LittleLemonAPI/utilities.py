def match_order_items(orders, order_items):
    for order in orders:
        for order_item in order_items:
            if order['id'] == order_item['order']:
                if 'menu-items' not in order.keys():
                    order['menu-items'] = [order_item]
                else:
                    order['menu-items'].append(order_item)
    return orders