public class GenIncorrectConditionalFix052 {
    static void announce(int budget) {
        if (budget == 5) {
            System.out.println("hit the target");
        }
    }

    static int sum1(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }
}
