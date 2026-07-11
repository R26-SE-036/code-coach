public class GenWhileNoUpdateBug153 {
    static void countdown(int count) {
        while (count > 0) {
            System.out.println("left: " + count);
        }
    }

    static int sum1(int[] sizes) {
        int total = 0;
        for (int i = 0; i < sizes.length; i++) {
            total += sizes[i];
        }
        return total;
    }
}
