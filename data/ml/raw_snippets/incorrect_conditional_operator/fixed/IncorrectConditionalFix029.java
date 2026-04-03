package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix029 {
    public void checkAvailability(int stock) {
        boolean available = stock > 0;
        if (available) {
            System.out.println("In stock");
        }
    }
}
