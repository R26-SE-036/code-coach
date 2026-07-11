public class GenIncorrectConditionalBug170 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void announce(int stock) {
        if (stock = 5) {
            System.out.println("hit the target");
        }
    }

    static int sum2(int[] marks) {
        int total = 0;
        for (int i = 0; i < marks.length; i++) {
            total += marks[i];
        }
        return total;
    }
}
