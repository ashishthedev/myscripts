INTEREST = .08
LIMIT = 100000
YEARS = 50
INITIAL = LIMIT

def main():
  principal = INITIAL
  for y in range(1, YEARS):
    newPrincipal = (principal)*(1 + INTEREST)
    interestGathered = round((newPrincipal - LIMIT*y)/100000, 3)
    raw_input("Year end {}: Rs.{}lakh Interest:{}".format(y, round(newPrincipal/100000, 3), interestGathered))
    principal = newPrincipal + LIMIT


if __name__ == "__main__":
  main()
