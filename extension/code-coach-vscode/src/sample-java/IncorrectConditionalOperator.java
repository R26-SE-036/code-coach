public class IncorrectConditionalOperator {
    public static void main(String[] args) {
        boolean passed = false;
        int score = 75;
        if (passed = score >= 50) {
            System.out.println("Pass");
        } else {
            System.out.println("Fail");
        }
    }
}
