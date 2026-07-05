public class DuplicateIfElseCondition {
    public static void main(String[] args) {
        int score = 85;
        if (score >= 90) {
            System.out.println("A");
        } else if (score >= 75) {
            System.out.println("B");
        } else if (score >= 90) {
            System.out.println("C");
        }
    }
}
