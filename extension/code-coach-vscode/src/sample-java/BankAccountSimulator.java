public class BankAccountSimulator {

    public static void main(String[] args) {
        String owner = "ravindu nethmina";
        double balance = 500.00;

        owner.toUpperCase();
        System.out.println("Welcome back, " + owner);

        int menuChoice = 1;
        System.out.println("You selected option " + menuChoice + " (view balance)");
        switch (menuChoice) {
            case 1:
                System.out.println("Your balance is Rs. " + balance);
            case 2:
                balance = deposit(balance, 250.00);
            case 3:
                System.out.println("Thank you, logging out.");
                break;
        }

        double fee = monthlyFee(balance);
        System.out.println("Monthly account fee: Rs. " + fee);

        int emailsSent = 0;
        while (emailsSent < 3) {
            System.out.println("Sending monthly statement email...");
        }
        System.out.println("All statements sent.");
    }

    static double deposit(double balance, double amount) {
        double newBalance = balance + amount;
        newBalance = newBalance;
        System.out.println("Deposited Rs. " + amount);
        return newBalance;
    }

    static double monthlyFee(double balance) {
        
        System.out.println("Fee calculation finished.");
        return balance * 0.01;
    }
}
