public class GenIncorrectConditionalFix119 {
    static void announce(int budget) {
        if (budget == 5) {
            System.out.println("hit the target");
        }
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
