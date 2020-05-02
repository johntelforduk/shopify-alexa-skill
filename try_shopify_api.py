# Try out the Shopify API class.

from shopify_alexa import Skill

this_skill = Skill()
this_skill.shop.get_store_info()

today = this_skill.date_as_str(delta_days=0)
two_days_ago = this_skill.date_as_str(delta_days=-2)
this_skill.shop.get_orders(from_date=two_days_ago, to_date=today)

chosen_date = this_skill.date_as_str(delta_days=0)
orders = this_skill.shop.orders_on_date(target_date=chosen_date)
print('Orders')
for each_order in orders:
    print('{}  {}'.format(each_order['created_at'], each_order['total_price']))

print()
print('number_orders_today =', this_skill.number_orders_today())
print('number_orders_yesterday =', this_skill.number_orders_yesterday())
print('gross_sales_today =', this_skill.gross_sales_today())
print('gross_sales_yesterday =', this_skill.gross_sales_yesterday())
print('most_recent_order =', this_skill.most_recent_order())
