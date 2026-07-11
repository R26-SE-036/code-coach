public class GenWhileNoUpdateBug130 {
    static void pump(boolean armed, int count) {
        while (!armed) {
            System.out.println(count);
            count++;
        }
    }
}
