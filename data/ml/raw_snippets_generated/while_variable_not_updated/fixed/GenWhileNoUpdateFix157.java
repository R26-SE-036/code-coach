public class GenWhileNoUpdateFix157 {
    static int sum1(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static void countdown(int quota) {
        while (quota > 0) {
            System.out.println("left: " + quota);
            quota--;
        }
    }
}
