package data.ml.raw_snippets.missing_break_in_switch.fixed;

public class MissingBreakFix003 {
    public static void main(String[] args) {
        int choice = 1;
        switch (choice) {
            case 1:
                System.out.println("Deposit selected");
                break;
            case 2:
                System.out.println("Withdraw selected");
                break;
            case 3:
                System.out.println("Balance selected");
                break;
            default:
                System.out.println("Invalid option");
        }
    }
}
