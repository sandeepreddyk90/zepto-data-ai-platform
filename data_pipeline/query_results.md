Scraped 133 books from 3 categories; GBP→INR rate: 105.5


## 01_where
```sql
SELECT title, price_gbp FROM books WHERE price_gbp BETWEEN 10 AND 20 ORDER BY price_gbp DESC LIMIT 10;
```

| title                                                   |   price_gbp |
|:--------------------------------------------------------|------------:|
| Lumberjanes Vol. 3: A Terrible Plan (Lumberjanes #9-12) |       19.92 |
| In a Dark, Dark Wood                                    |       19.63 |
| Fruits Basket, Vol. 7 (Fruits Basket #7)                |       19.57 |
| This One Summer                                         |       19.49 |
| The Cuckoo's Calling (Cormoran Strike #1)               |       19.21 |
| Pop Gun War, Volume 1: Gift                             |       18.97 |
| Y: The Last Man, Vol. 1: Unmanned (Y: The Last Man #1)  |       18.51 |
| Lilac Girls                                             |       17.28 |
| Camp Midnight                                           |       17.08 |
| A Spy's Devotion (The Regency Spies of London #1)       |       16.97 |


## 02_distinct
```sql
SELECT DISTINCT c.category_name FROM books b JOIN categories c ON b.category_id = c.category_id ORDER BY c.category_name;
```

| category_name      |
|:-------------------|
| Historical Fiction |
| Mystery            |
| Sequential Art     |


## 03_rating
```sql
SELECT title, rating FROM books WHERE rating IN (4, 5) ORDER BY rating DESC, title LIMIT 12;
```

| title                                                                             |   rating |
|:----------------------------------------------------------------------------------|---------:|
| A Flight of Arrows (The Pathfinders #2)                                           |        5 |
| A Spy's Devotion (The Regency Spies of London #1)                                 |        5 |
| A Time of Torment (Charlie Parker #14)                                            |        5 |
| Batman: The Dark Knight Returns (Batman)                                          |        5 |
| Between Shades of Gray                                                            |        5 |
| Bleach, Vol. 1: Strawberry and the Soul Reapers (Bleach #1)                       |        5 |
| El Deafo                                                                          |        5 |
| Fruits Basket, Vol. 1 (Fruits Basket #1)                                          |        5 |
| Fruits Basket, Vol. 2 (Fruits Basket #2)                                          |        5 |
| Mrs. Houdini                                                                      |        5 |
| Princess Jellyfish 2-in-1 Omnibus, Vol. 01 (Princess Jellyfish 2-in-1 Omnibus #1) |        5 |
| Rat Queens, Vol. 1: Sass & Sorcery (Rat Queens (Collected Editions) #1-5)         |        5 |


## 04_stock
```sql
SELECT in_stock, COUNT(*) AS count FROM books GROUP BY in_stock ORDER BY in_stock DESC;
```

|   in_stock |   count |
|-----------:|--------:|
|          1 |     133 |


## 05_join
```sql
SELECT b.title, b.rating, b.price_gbp, c.category_name FROM books b JOIN categories c ON b.category_id = c.category_id WHERE b.rating = 5 ORDER BY c.category_name, b.title LIMIT 20;
```

| title                                                                             |   rating |   price_gbp | category_name      |
|:----------------------------------------------------------------------------------|---------:|------------:|:-------------------|
| A Flight of Arrows (The Pathfinders #2)                                           |        5 |       55.53 | Historical Fiction |
| A Spy's Devotion (The Regency Spies of London #1)                                 |        5 |       16.97 | Historical Fiction |
| Between Shades of Gray                                                            |        5 |       20.79 | Historical Fiction |
| Mrs. Houdini                                                                      |        5 |       30.25 | Historical Fiction |
| The Passion of Dolssa                                                             |        5 |       28.32 | Historical Fiction |
| The Red Tent                                                                      |        5 |       35.66 | Historical Fiction |
| Voyager (Outlander #3)                                                            |        5 |       21.07 | Historical Fiction |
| While You Were Mine                                                               |        5 |       41.32 | Historical Fiction |
| A Time of Torment (Charlie Parker #14)                                            |        5 |       48.35 | Mystery            |
| The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1)          |        5 |       52.3  | Mystery            |
| The Girl You Lost                                                                 |        5 |       12.29 | Mystery            |
| The Silkworm (Cormoran Strike #2)                                                 |        5 |       23.05 | Mystery            |
| What Happened on Beale Street (Secrets of the South Mysteries #2)                 |        5 |       25.37 | Mystery            |
| Batman: The Dark Knight Returns (Batman)                                          |        5 |       15.38 | Sequential Art     |
| Bleach, Vol. 1: Strawberry and the Soul Reapers (Bleach #1)                       |        5 |       34.65 | Sequential Art     |
| El Deafo                                                                          |        5 |       57.62 | Sequential Art     |
| Fruits Basket, Vol. 1 (Fruits Basket #1)                                          |        5 |       40.28 | Sequential Art     |
| Fruits Basket, Vol. 2 (Fruits Basket #2)                                          |        5 |       11.64 | Sequential Art     |
| Princess Jellyfish 2-in-1 Omnibus, Vol. 01 (Princess Jellyfish 2-in-1 Omnibus #1) |        5 |       13.61 | Sequential Art     |
| Rat Queens, Vol. 1: Sass & Sorcery (Rat Queens (Collected Editions) #1-5)         |        5 |       46.96 | Sequential Art     |


## Equivalent join results (SQL `pd.read_sql` / pandas `pd.merge`)

| title                                                                             |   rating |   price_gbp | category_name      |
|:----------------------------------------------------------------------------------|---------:|------------:|:-------------------|
| A Flight of Arrows (The Pathfinders #2)                                           |        5 |       55.53 | Historical Fiction |
| A Spy's Devotion (The Regency Spies of London #1)                                 |        5 |       16.97 | Historical Fiction |
| Between Shades of Gray                                                            |        5 |       20.79 | Historical Fiction |
| Mrs. Houdini                                                                      |        5 |       30.25 | Historical Fiction |
| The Passion of Dolssa                                                             |        5 |       28.32 | Historical Fiction |
| The Red Tent                                                                      |        5 |       35.66 | Historical Fiction |
| Voyager (Outlander #3)                                                            |        5 |       21.07 | Historical Fiction |
| While You Were Mine                                                               |        5 |       41.32 | Historical Fiction |
| A Time of Torment (Charlie Parker #14)                                            |        5 |       48.35 | Mystery            |
| The Bachelor Girl's Guide to Murder (Herringford and Watts Mysteries #1)          |        5 |       52.3  | Mystery            |
| The Girl You Lost                                                                 |        5 |       12.29 | Mystery            |
| The Silkworm (Cormoran Strike #2)                                                 |        5 |       23.05 | Mystery            |
| What Happened on Beale Street (Secrets of the South Mysteries #2)                 |        5 |       25.37 | Mystery            |
| Batman: The Dark Knight Returns (Batman)                                          |        5 |       15.38 | Sequential Art     |
| Bleach, Vol. 1: Strawberry and the Soul Reapers (Bleach #1)                       |        5 |       34.65 | Sequential Art     |
| El Deafo                                                                          |        5 |       57.62 | Sequential Art     |
| Fruits Basket, Vol. 1 (Fruits Basket #1)                                          |        5 |       40.28 | Sequential Art     |
| Fruits Basket, Vol. 2 (Fruits Basket #2)                                          |        5 |       11.64 | Sequential Art     |
| Princess Jellyfish 2-in-1 Omnibus, Vol. 01 (Princess Jellyfish 2-in-1 Omnibus #1) |        5 |       13.61 | Sequential Art     |
| Rat Queens, Vol. 1: Sass & Sorcery (Rat Queens (Collected Editions) #1-5)         |        5 |       46.96 | Sequential Art     |

Equality: **True** (checked by `pd.testing.assert_frame_equal`).

## Second `pd.read_sql` result

| title                                                   |   price_gbp |
|:--------------------------------------------------------|------------:|
| Lumberjanes Vol. 3: A Terrible Plan (Lumberjanes #9-12) |       19.92 |
| In a Dark, Dark Wood                                    |       19.63 |
| Fruits Basket, Vol. 7 (Fruits Basket #7)                |       19.57 |
| This One Summer                                         |       19.49 |
| The Cuckoo's Calling (Cormoran Strike #1)               |       19.21 |
| Pop Gun War, Volume 1: Gift                             |       18.97 |
| Y: The Last Man, Vol. 1: Unmanned (Y: The Last Man #1)  |       18.51 |
| Lilac Girls                                             |       17.28 |
| Camp Midnight                                           |       17.08 |
| A Spy's Devotion (The Regency Spies of London #1)       |       16.97 |
