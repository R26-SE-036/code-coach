package data.ml.raw_snippets.incorrect_conditional_operator.buggy;

public class IncorrectConditionalBug029 {
    public void checkAvailability(int stock) {
        boolean available = false;
        if (available = stock > 0) {
            System.out.println("In stock");
        }
    }
}
