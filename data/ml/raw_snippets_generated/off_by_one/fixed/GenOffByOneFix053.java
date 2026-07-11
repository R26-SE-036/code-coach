public class GenOffByOneFix053 {
    static int countAbove(int[] ages, int threshold) {
        int hits = 0;
        for (int i = 0; i < ages.length; i++) {
            if (ages[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static int drain1(int steps) {
        int handled = 0;
        while (steps > 0) {
            handled += steps;
            steps--;
        }
        return handled;
    }
}
