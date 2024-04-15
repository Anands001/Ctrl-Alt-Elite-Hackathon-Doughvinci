from datetime import datetime, timedelta
import random

class Order:
    def __init__(self, order_id, kitchen_id, customer_id, pickup_time, location):
        self.order_id = order_id
        self.kitchen_id = kitchen_id
        self.customer_id = customer_id
        self.pickup_time = pickup_time
        self.location = location


class Rider:
    def __init__(self, rider_id, current_location):
        self.rider_id = rider_id
        self.current_location = current_location


class DeliveryBatch:
    def __init__(self):
        self.orders = []
        self.destination = None


def calculate_distance(location1, location2):
    # Calculate Manhattan distance between two locations
    x1, y1 = location1
    x2, y2 = location2
    return abs(x2 - x1) + abs(y2 - y1)


def group_orders(orders):
    grouped_orders = []

    def group_orders_by_rule(order_key_func):
        order_groups = {}
        for order in orders:
            key = order_key_func(order)
            if key in order_groups:
                order_groups[key].append(order)
            else:
                order_groups[key] = [order]
        for orders_list in order_groups.values():
            if len(orders_list) > 1:
                sorted_orders = sorted(orders_list, key=lambda x: datetime.strptime(x.pickup_time, '%I:%M %p'))
                group = [sorted_orders[0]]
                for i in range(1, len(sorted_orders)):
                    prev_time = datetime.strptime(sorted_orders[i - 1].pickup_time, '%I:%M %p')
                    current_time = datetime.strptime(sorted_orders[i].pickup_time, '%I:%M %p')
                    time_difference = (current_time - prev_time).total_seconds() / 60  # Convert to minutes
                    if time_difference <= 10:
                        group.append(sorted_orders[i])
                    else:
                        grouped_orders.append(group)
                        group = [sorted_orders[i]]
                grouped_orders.append(group)

    # Rule #1: Group orders from the same kitchen and customer with similar ready times
    group_orders_by_rule(lambda order: (order.kitchen_id, order.customer_id))

    # Rule #2: Group orders from two different kitchens to the same customer
    group_orders_by_rule(lambda order: order.customer_id)

    # Rule #3: Group orders from the same kitchen to two different customers
    group_orders_by_rule(lambda order: order.kitchen_id)

    return grouped_orders


def optimize_route(delivery_batch):
    orders = delivery_batch.orders
    if not orders:
        return

    # Calculate the centroid of the orders' locations as the destination
    centroid_x = sum(order.location[0] for order in orders) / len(orders)
    centroid_y = sum(order.location[1] for order in orders) / len(orders)
    delivery_batch.destination = (centroid_x, centroid_y)


def assign_batches_to_riders(delivery_batches, riders):
    assigned_orders = set()  # Track assigned orders
    assigned_batches = {rider.rider_id: [] for rider in riders}

    # Sort the riders by their current location
    riders.sort(key=lambda rider: rider.current_location)

    # Assign batches to riders based on their availability and distance
    for batch in delivery_batches:
        closest_rider = None
        min_distance = float('inf')

        # Find the closest available rider to the batch destination
        for rider in riders:
            if batch.destination not in assigned_orders:  # Check if the batch destination has been assigned
                distance_to_batch = calculate_distance(rider.current_location, batch.destination)
                if distance_to_batch < min_distance:
                    min_distance = distance_to_batch
                    closest_rider = rider

        if closest_rider:
            assigned_batches[closest_rider.rider_id].append(batch)
            assigned_orders.add(batch.destination)  # Mark the destination as assigned

    return assigned_batches


# Generate random orders
def generate_orders(num_orders):
    orders = []
    for i in range(1, num_orders + 1):
        order_id = i
        kitchen_id = f'kitchen{random.randint(1, 5)}'  # Corrected usage of random.randint
        customer_id = f'customer{random.randint(1, 20)}'
        pickup_time = (datetime.now() + timedelta(minutes=random.randint(0, 120))).strftime('%I:%M %p')
        location = (random.uniform(0, 10), random.uniform(0, 10))  # Random location
        orders.append(Order(order_id, kitchen_id, customer_id, pickup_time, location))
    return orders


# Generate random riders
def generate_riders(num_riders):
    riders = []
    for i in range(1, num_riders + 1):
        rider_id = i
        current_location = (random.uniform(0, 10), random.uniform(0, 10))  # Random location
        riders.append(Rider(rider_id, current_location))
    return riders


# Generate a sample dataset
def generate_dataset(num_orders, num_riders):
    orders = generate_orders(num_orders)
    riders = generate_riders(num_riders)
    return orders, riders


if __name__ == "__main__":
    # Generate a dataset with 20 orders and 5 riders
    orders, riders = generate_dataset(20, 5)

    # Step 1: Group orders based on rules
    grouped_orders = group_orders(orders)

    # Step 2: Optimize route for each delivery batch
    delivery_batches = []
    for group in grouped_orders:
        delivery_batch = DeliveryBatch()
        delivery_batch.orders = group
        optimize_route(delivery_batch)
        delivery_batches.append(delivery_batch)

    # Step 3: Assign delivery batches to riders
    assigned_batches = assign_batches_to_riders(delivery_batches, riders)

    # Print the assigned batches in a more understandable format
    print("Assigned Batches to Riders:")
    for rider_id, batches in assigned_batches.items():
        print(f"Rider ID: {rider_id}")
        if (rider_id < len(riders)):
            print(f"Current Location: {riders[rider_id].current_location}")
        for batch in batches:
            print(f"Batch Destination: {batch.destination}")
            print("Orders in the Batch:")
            for order in batch.orders:
                print(
                    f"- Order ID: {order.order_id}, Kitchen ID: {order.kitchen_id}, Customer ID: {order.customer_id}, Pickup Time: {order.pickup_time}, Location: {order.location}")
            print()
