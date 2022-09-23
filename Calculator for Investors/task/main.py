from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, create_engine
from sqlalchemy.orm import sessionmaker, Query
import csv

columns = ('ticker', 'name', 'sector', 'ebitda', 'sales', 'net_profit', 'market_price', 'net_debt', 'assets', 'equity',
           'cash_equivalents', 'liabilities')


def validate_choice(valid_options, exit_code="0"):
    choice = input("Enter an option: ")
    if choice in valid_options or choice == exit_code:
        return choice
    elif choice not in valid_options:
        print("Invalid option!")


def main_menu():
    print("MAIN MENU")
    print(0, "Exit")
    print(1, "CRUD operations")
    print(2, "Show top ten companies by criteria")
    choice = validate_choice(["1", "2"])
    if choice == "0":
        print("Have a nice day!")
        return
    else:
        if choice == "1":
            crud_menu()
        elif choice == "2":
            top_ten_menu()
    main_menu()


def crud_menu():
    print("CRUD MENU")
    print(0, "Back")
    print(1, "Create a company")
    print(2, "Read a company")
    print(3, "Update a company")
    print(4, "Delete a company")
    print(5, "List all companies")
    choice = validate_choice([str(i) for i in range(1, 6)])
    if choice == "1":
        create()
    elif choice in ("2", "3", "4"):
        read_update_delete(choice)
    elif choice == "5":
        list_companies()


def list_companies():
    with Session() as session:
        print("COMPANY LIST")
        for company in session.query(Companies).order_by(Companies.ticker):
            if company.ticker == 'AXP':
                continue
            print(company.ticker, company.name, company.sector)


def create():
    data = get_data("create")

    with Session() as session:
        session.add(Companies(**sanitize_dict({k: v for k, v in data.items() if k in ('ticker', 'name', 'sector')})))
        session.add(Financial(**sanitize_dict({k: v for k, v in data.items() if k not in ('name', 'sector')})))

        try:
            session.commit()
        except Exception as e:
            print(e)
        else:
            print("Company created successfully!")


def get_data(action):
    if action == 'update':
        return {i: get_input(i) for i in columns if i not in ("name", "sector", "ticker")}
    elif action == "create":
        return {i: get_input(i) for i in columns}


def read_update_delete(choice):
    with Session() as session:
        company_name = input("Enter company name: ")
        query = session.query(Companies).filter(Companies.name.like(f"%{company_name}%"))
        if bool(session.query(Companies).filter(Companies.name.like(f"%{company_name}%")).first()):
            companies = {}
            for idx, company in enumerate(query):
                companies[idx] = [company.ticker, company.name]
                print(idx, company.name)

            company_number = int(input("Enter company number:"))
            if choice == "2":
                company_data = session.query(Financial).filter(Financial.ticker == companies[company_number][0])
                calculate_indicators(company_data, companies[company_number])
            elif choice == "3":
                session.query(Financial).filter(Financial.ticker == companies[company_number][0])\
                    .update(sanitize_dict(get_data("update")))
            elif choice == "4":
                session.query(Companies).filter(Companies.ticker == companies[company_number][0]).delete()
                session.query(Financial).filter(Financial.ticker == companies[company_number][0]).delete()

            if choice in ("3", "4"):
                try:
                    session.commit()
                except Exception as e:
                    print(e)
                else:
                    print(f"Company {'deleted' if choice == '4' else 'updated'} successfully!")
        else:
            print("Company not found!")
        print()


def calculate_indicators(company_datas, company):
    for company_data in company_datas:
        print(company[0], company[1])
        print("P/E =", format_decimals(company_data.market_price, company_data.net_profit))
        print("P/S =", format_decimals(company_data.market_price, company_data.sales))
        print("P/B =", format_decimals(company_data.market_price, company_data.assets))
        print("ND/EBITDA =", format_decimals(company_data.net_debt, company_data.ebitda))
        print("ROE =", format_decimals(company_data.net_profit, company_data.equity))
        print("ROA =", format_decimals(company_data.net_profit, company_data.assets))
        print("L/A =", format_decimals(company_data.liabilities, company_data.assets))


def format_decimals(num1, num2, places=2):
    if not num2:
        return None
    return ''.join(["{:.", str(places), "f}"]).format(0 if not num1 else num1 / num2)


def get_input(col):
    if col == "ticker":
        data = in_the_format(col, 'MOON')
    elif col == 'name':
        data = in_the_format('company', 'Moon Corp')
    elif col == 'sector':
        data = in_the_format('industries', 'Technology')
    elif col == "net_debt":
        data = in_the_format('net_dept', 'Technology')
    else:
        data = in_the_format(col, '987654321')
    return data


def in_the_format(col, sample):
    return input(f"Enter {col.replace('_', ' ')} (in the format '{sample}'):")


def top_ten_menu():
    print("TOP TEN MENU")
    print(0, "Back")
    print(1, "List by ND/EBITDA")
    print(2, "List by ROE")
    print(3, "List by ROA")
    choice = validate_choice([str(i) for i in range(1, 4)])
    if choice:
        list_by_param(choice)


def list_by_param(choice):
    with Session() as session:
        if choice == '1':
            opt = {
                "using": "ND/EBITDA",
                "formula": Financial.net_debt / Financial.ebitda
            }
        elif choice == "2":
            opt = {
                "using": "ROE",
                "formula": Financial.net_profit / Financial.equity
            }
        elif choice == "3":
            opt = {
                "using": "ROA",
                "formula": Financial.net_profit / Financial.assets
            }

        print("TICKER", opt.get("using"))
        for data in session.query(Financial.ticker, opt.get("formula").label("result"))\
                .order_by(opt.get("formula").label("result").desc()).limit(10):
            print(data.ticker, format_result(data.result))


def format_result(result):
    return round(float("{:.2f}".format(result)), 2)


def sanitize_dict(sample_dict):
    return {key: val if val else None for key, val in sample_dict.items()}


Base = declarative_base()
engine = create_engine("sqlite:///investor.db")
Session = sessionmaker(bind=engine)


class Companies(Base):
    __tablename__ = "companies"
    ticker = Column(String, primary_key=True)
    name = Column(String(30))
    sector = Column(String(30))


class Financial(Base):
    __tablename__ = "financial"
    ticker = Column(String, primary_key=True)
    ebitda = Column(Float, default=None)
    sales = Column(Float, default=None)
    net_profit = Column(Float, default=None)
    market_price = Column(Float, default=None)
    net_debt = Column(Float, default=None)
    assets = Column(Float, default=None)
    equity = Column(Float, default=None)
    cash_equivalents = Column(Float, default=None)
    liabilities = Column(Float, default=None)


def load_csv():
    with open("test/financial.csv") as financial, open("test/companies.csv") as companies, Session() as session:
        finance_data = csv.DictReader(financial)
        companies_data = csv.DictReader(companies)

        for data in finance_data:
            if not bool(session.query(Financial).filter(Financial.ticker == data.get("ticker")).first()):
                session.add(Financial(**sanitize_dict(data)))
        for data in companies_data:
            if not bool(session.query(Companies).filter(Companies.ticker == data.get("ticker")).first()):
                session.add(Companies(**sanitize_dict(data)))

        session.commit()


Base.metadata.create_all(engine)
load_csv()
print("Welcome to the Investor Program!")
main_menu()


