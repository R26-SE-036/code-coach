public class GenOffByOneFix082 {
    static boolean isEven1(int budget) {
        return budget % 2 == 0;
    }

    static int addUp(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }
}
