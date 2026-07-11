public class GenCleanBoundaryMinusOne017 {
    static void printAll1(int[] ratings) {
        for (int value : ratings) {
            System.out.println(value);
        }
    }

    static int drain2(int limit) {
        int handled = 0;
        while (limit > 0) {
            handled += limit;
            limit--;
        }
        return handled;
    }

    static int sum3(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static int tally(int[] weights) {
        int total = 0;
        for (int i = 0; i <= weights.length - 1; i++) {
            total += weights[i];
        }
        return total;
    }
}
