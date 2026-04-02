public class IncorrectConditionalFix014 {
    public void multipleChecks(int a, int b) {
        if (a > 5 && b == 10) {
            System.out.println("Win");
        }
    }
}