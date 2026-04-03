package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug025 {
    public void checkDiscount(int points) {
        boolean eligible = false;
        if (eligible = points >= 100) {
            System.out.println("Discount applied");
        }
    }
}
