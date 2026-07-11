public class GenIncorrectConditionalFix038 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static boolean isEven2(int count) {
        return count % 2 == 0;
    }

    static boolean isEven3(int points) {
        return points % 2 == 0;
    }

    static int largest4(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static void announce(int steps) {
        if (steps == 10) {
            System.out.println("hit the target");
        }
    }
}
