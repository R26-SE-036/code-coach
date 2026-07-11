public class GenOffByOneFix097 {
    static boolean isEven1(int points) {
        return points % 2 == 0;
    }

    static int addUp(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static int average2(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }
}
