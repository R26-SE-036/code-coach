package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix017 {
    public void checkBalance(double balance) {
        boolean overdrawn = balance < 0;
        if (overdrawn) {
            System.out.println("Account overdrawn");
        }
    }
}
