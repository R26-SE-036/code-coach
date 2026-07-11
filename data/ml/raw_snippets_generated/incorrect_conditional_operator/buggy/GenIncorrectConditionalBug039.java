public class GenIncorrectConditionalBug039 {
    static int sum1(int[] scores) {
        int total = 0;
        for (int i = 0; i < scores.length; i++) {
            total += scores[i];
        }
        return total;
    }

    static void announce(int steps) {
        if (steps = 10) {
            System.out.println("hit the target");
        }
    }

    static void printAll2(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }
}
