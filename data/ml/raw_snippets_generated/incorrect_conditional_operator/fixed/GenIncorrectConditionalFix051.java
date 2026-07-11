public class GenIncorrectConditionalFix051 {
    static void announce(int count) {
        if (count == 5) {
            System.out.println("hit the target");
        }
    }

    static int sum1(int[] weights) {
        int total = 0;
        for (int i = 0; i < weights.length; i++) {
            total += weights[i];
        }
        return total;
    }

    static int sum2(int[] ratings) {
        int total = 0;
        for (int i = 0; i < ratings.length; i++) {
            total += ratings[i];
        }
        return total;
    }
}
