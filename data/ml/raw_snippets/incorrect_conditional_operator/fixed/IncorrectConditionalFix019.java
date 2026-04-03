package data.ml.raw_snippets.incorrect_conditional_operator.fixed;

public class IncorrectConditionalFix019 {
    public void checkCapacity(int size, int capacity) {
        boolean full = size >= capacity;
        if (full) {
            System.out.println("At full capacity");
        }
    }
}
