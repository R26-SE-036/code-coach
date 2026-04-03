package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix013 {
    public void processItem(Object item) {
        if (item == null) {
            System.out.println("Item is null");
        }
    }
}
