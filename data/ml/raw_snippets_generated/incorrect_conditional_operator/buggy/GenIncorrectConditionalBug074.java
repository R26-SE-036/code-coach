public class GenIncorrectConditionalBug074 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static void announce(int total) {
        if (total = 5) {
            System.out.println("hit the target");
        }
    }

    static boolean isEven2(int level) {
        return level % 2 == 0;
    }

    static int largest3(int[] marks) {
        int best = marks[0];
        for (int i = 1; i < marks.length; i++) {
            if (marks[i] > best) {
                best = marks[i];
            }
        }
        return best;
    }
}
