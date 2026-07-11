public class GenWhileNoUpdateFix058 {
    static void countdown(int points) {
        while (points > 0) {
            System.out.println("left: " + points);
            points--;
        }
    }

    static void printAll1(int[] weights) {
        for (int value : weights) {
            System.out.println(value);
        }
    }

    static int largest2(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
    }
}
