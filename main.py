import pyodbc
import maskpass
import random

Server = 'DESKTOP-99H3564\CRABIBARA'
Database = 'business'
UID = 'sa'
PWD = 123

connection = pyodbc.connect('Driver={SQL Server};'
                             f'Server={Server};'
                             f'Database={Database};'
                             f'UID={UID};'
                             f'PWD={PWD};')
cursor = connection.cursor()

def main():
    chose = int(input("Выберите действие:\n1-Войти в аккаунт\n2-Зарегистрироваться\n"))
    match chose:
        case 1: authorization()
        case 2: registration()

def authorization():
    login = input("Введите логин: ")
    password = maskpass.advpass("Введите пароль: ", mask="*")
    results = getUsers()
    for row in results:
        if (login == str(row[1]) and password == str(row[4])): 
            print("Авторизация прошла успешно!")
            getAccountData(login)
            return
    print("Неверный логин или пароль!")

def registration():
    results = getUsers()
    login = input("Придумайте логин: ")
    for row in results:
        if (login == str(row[1])):
            print("Аккаунт с таким логином уже зарегистрирован!")
            return
    password = input("Придумайте пароль: ")
    phoneNum = input("Введите номер телефона (формат: 7(XXX)XXX-XX-XX): ")
    for row in results:
        if (phoneNum == str(row[5])):
            print("Аккаунт с таким номером телефона уже зарегистрирован!")
            return
    balance = 880*random.randint(2, 5)
    SQLQuery = (f"""
                INSERT INTO [User] ([ID_Role], [ID_Card], [Login], [Password], [Balance], [Phone_Number])
                VALUES (1, NULL, '{login}', '{password}', {balance}, '{phoneNum}');
                """)
    cursor.execute(SQLQuery)
    connection.commit()
    getAccountData(login)

def getUsers():
    SQLQuery = ("""
                SELECT * FROM [User]
                """)
    cursor.execute(SQLQuery)
    results = cursor.fetchall()
    return results

def getAccountData(login):
    results = getUsers()
    for row in results:
        if (login == str(row[1])):
            balance = row[5]
            if (row[5] < 880):
                balance = 880*random.randint(2, 5)
                SQLQuery = (f"""
                            UPDATE [User] SET [Balance] = {balance} WHERE [Login] = '{login}'
                            """)
                cursor.execute(SQLQuery)
                connection.commit()
            print(f'Логин: {str(row[1])}\nНомер телефона: {str(row[6])}\nБаланс: {balance}₽')
            if (row[2] == 1): 
                chose = int(input("Выберите действие:\n1-Купить ингредиенты\n2-Просмотреть историю покупок\n"))
                match chose:
                    case 1: ingredientBuying(row[0])
                    case 2: historyBuying(row[0])
            else: 
                chose = int(input("Выберите действие:\n1-Купить блюдо\n2-Просмотреть историю покупок\n"))
                match chose:
                    case 1: dishBuying(row[0])
                    case 2: historyBuying(row[0])

def ingredientBuying(accountID):
    results = getIngredients()
    count = 0
    print("Выберите продукт:")
    for row in results:
        count += 1
        print(f'{count}-{str(row[1])}-{str(row[4])}₽')
    chose = int(input())
    amount = int(input("Введите количество покупаемого товара:\n"))
    for row in results:
        if (chose == row[0]):
            cost = row[4]*amount
    user = getUsers()
    for row in user:
        if (accountID == row[0]):
            if (cost > row[5]):
                print("На балансе недостаточно средств!")
                return
            else:
                SQLQuery = (f"""
                            INSERT INTO [Purchase] ([ID_User], [ID_Object], [ID_Dish], [ID_Ingredient], [Cost], [Amount])
                            VALUES ({accountID}, NULL, NULL, {chose}, {cost}, '{amount}');
                            """)
                cursor.execute(SQLQuery)
                connection.commit()
                SQLQuery = (f"""
                            UPDATE [User] SET [Balance] = [Balance] - {cost} WHERE [ID_User] = {accountID}
                            """)
                cursor.execute(SQLQuery)
                connection.commit()
                SQLQuery = (f"""
                            UPDATE [Ingredient] SET [Amount] = [Amount] + {amount} WHERE [ID_Ingredient] = {chose}
                            """)
                cursor.execute(SQLQuery)
                connection.commit()
                print("Покупка успешно произведена!")
                getAccountData(row[1])

def dishBuying(accountID):
    results = getIngredients()
    count = 0
    for row in results:
        count += 1
        print(f"{count}-{str(row[1])}")
    print("Введите номера ингредиентов, которые вы хотите убрать из блюда (если вы завершили ввод введите 0):")
    list = []
    i = 0
    for row in results:
        ingredient = int(input())
        if (ingredient != 0): 
            if (ingredient < 0 or ingredient > 7): print("Вы ввели недопустимое число!")                
            else: list.insert(i, ingredient)
            i += 1
        else: break
    amount = int(input("введите количество покупаемого блюда:\n"))
    user = getUsers()
    for row in results:
        for element in list:
            if (row[0] == element):
                SQLQuery = (f"""
                            UPDATE [Ingredient] SET [Amount] = [Amount] + {amount} WHERE [ID_Ingredient] = {row[0]}
                            """)
                cursor.execute(SQLQuery)
                connection.commit()
    for row in user:
        if (accountID == row[0]):
            price = 880*amount
            if (price > row[5]):
                print("На балансе недостаточно средств!")
                return
            else: 
                if (amount >= 5):
                    print("Вы купили 5 блюд, вы получаете скидку 5% :D")
                    price = price-price/100*5
                for row in results:
                    if (row[3] == 0): 
                        print(f"Ингредиент '{row[1]}' закончился, его стоимость будет исключена из конечной цены")
                        price = price - row[4]
                    else:
                        SQLQuery = (f"""
                                    UPDATE [Ingredient] SET [Amount] = [Amount] - {amount} WHERE [ID_Ingredient] = {row[0]}
                                    """)
                        cursor.execute(SQLQuery)
                        connection.commit()
                object = random.randint(1, 5)
                attent = random.randint(1, 5)
                if (attent == object):
                    print("Вы заметили автомобильную шину в вашем блюде!\nВам полагается скидка 30%, если вы её съедите ;-) (шутка, не ешьте)")
                    price = price-(price/100*30)
                    defect = "Автомобильная шина - скидка 30%"
                if (object == 3): object = 1
                else: 
                    object = 'NULL'
                    defect = ''

                SQLQuery = (f"""
                            UPDATE [User] SET [Balance] = [Balance] - {price} WHERE [ID_User] = {accountID}
                            """)
                cursor.execute(SQLQuery)
                connection.commit()
                SQLQuery = (f"""
                            UPDATE [User] SET [Balance] = [Balance] + {price} WHERE [ID_User] = 1
                            """)
                cursor.execute(SQLQuery)
                connection.commit()
                SQLQuery = (f"""
                            INSERT INTO [Purchase] ([ID_User], [ID_Object], [ID_Dish], [ID_Ingredient], [Cost], [Amount])
                            VALUES ({accountID}, {object}, 1, NULL, {price}, {amount});
                            """)
                cursor.execute(SQLQuery)
                connection.commit()
                print(f"Покупка успешно произведена! \nВы купили Сосиски в пилке на {price}₽") 
                my_file = open("Check.txt", "w+")
                my_file.write(f"Сосиски в пилке\nЦена: {price}рублей\nКоличество: {amount}\n{defect}")
                my_file.close()
    
def getIngredients():
    SQLQuery = ("""
                SELECT * FROM [Ingredient]
                """)
    cursor.execute(SQLQuery)
    results = cursor.fetchall()
    return results

def historyBuying(accountID):
    SQLQuery = (f"""
        SELECT [Ingredient].[Name_Ingredient], [Purchase].[Cost], [Purchase].[Amount] 
        FROM [Purchase] 
        JOIN [User] ON [User].[ID_User] = [Purchase].[ID_User] 
        JOIN [Ingredient] ON [Ingredient].[ID_Ingredient] = [Purchase].[ID_Ingredient]
        WHERE [Purchase].[ID_User] = {accountID}
    """)
    cursor.execute(SQLQuery)
    results = cursor.fetchall()
    for row in results:
        ingredient = row[0]
        cost = row[1]
        amount = row[2]
        print(f"Ингредиент: {str(ingredient)}, цена: {str(cost)}, количество: {str(amount)}")

main()

connection.close()