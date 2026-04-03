package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug017 {
    public void checkBalance(double balance) {
        boolean overdrawn = false;
        if (overdrawn = balance < 0) {
            System.out.println("Account overdrawn");
        }
    }
}
