package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix025 {
    public void checkDiscount(int points) {
        boolean eligible = points >= 100;
        if (eligible) {
            System.out.println("Discount applied");
        }
    }
}
