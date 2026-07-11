public class GenWhileNoUpdateBug048 {
    static int largest1(int[] ages) {
        int best = ages[0];
        for (int i = 1; i < ages.length; i++) {
            if (ages[i] > best) {
                best = ages[i];
            }
        }
        return best;
    }

    static void pump(boolean running, int count) {
        while (!running) {
            System.out.println(count);
            count++;
        }
    }
}
